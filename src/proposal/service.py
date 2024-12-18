from proposal.methods.evaluation_methods import volume_evaluation, content_evaluation, regulation_evaluation
from proposal.methods.generation_methods import content_feedback, regulation_feedback, summary_generator

from proposal.prompts.generation_prompt import GenerationPrompt
from proposal.prompts.evaluation_prompt import EvaluationPrompt

from proposal.schemas import ProposalEvaluationRequestDto, ProposalEvaluationResponseDto, SummaryGenerationRequestDto, FeedbackDto, SummaryDto

SEP = "[SEP]"


def proposal_evaluation(request: ProposalEvaluationRequestDto) -> ProposalEvaluationResponseDto:
    # Proposal from the user
    proposal = request.title + SEP \
        + request.content + SEP \
        + request.media_type + SEP \
        + str(request.proposal_score) + SEP \
        + str(request.additional_features)
    proposal = proposal.replace("\n", "")

    # Prompts
    # for evaluation
    evaluation_prompt = EvaluationPrompt
    content_evaluation_prompt = evaluation_prompt.content_evaluation_prompt.value
    regulation_evaluation_prompt = evaluation_prompt.regulation_evaluation_prompt.value

    # for feedback generation
    generation_prompt = GenerationPrompt
    content_feedback_prompt = generation_prompt.content_feedback_prompt.value
    regulation_feedback_prompt = generation_prompt.regulation_feedback_prompt.value
    summary_generation_prompt = generation_prompt.summary_generation_prompt.value

    # Volume Check
    if (volume_evaluation(proposal=proposal, media_type=request.media_type)):
        return ProposalEvaluationResponseDto(
            evaluation_result=0,
            feedback=FeedbackDto(
                feedback_type=0,
                current_score=0,
                comment="기획안을 평가할 내용이 부족하여 더 이상의 평가가 불가능합니다.",
                violations=[]
            ),
            summary=SummaryDto(
                title="",
                content="",
                keyword=[]
            )
        )

    # Content Check
    content_evaluation_result = content_evaluation(
        proposal,
        content_evaluation_prompt
    )

    total_score = float(content_evaluation_result['message']) + float(
        content_evaluation_result['target']) + float(content_evaluation_result['relevance'])

    evaluated_proposal = "Message: " + content_evaluation_result['message'] + "Target: " + \
        content_evaluation_result['target'] + "Relevance: " + \
        content_evaluation_result['relevance'] + SEP + proposal

    if (total_score <= 65.0):
        generated_feedback = content_feedback(
            content_feedback_prompt=content_feedback_prompt,
            proposal=evaluated_proposal
        )

        return ProposalEvaluationResponseDto(
            evaluation_result=0,
            feedback=FeedbackDto(
                feedback_type=1,
                current_score=total_score,
                comment=generated_feedback,
                violations=[]
            ),
            summary=SummaryDto(
                title="",
                content="",
                current_score=0.0,
                keyword=[]
            )
        )

    # Regulation Check
    regulation_evaluation_result = regulation_evaluation(
        proposal=proposal,
        regulation_evaluation_prompt=regulation_evaluation_prompt
    )

    appropriate = bool(regulation_evaluation_result['appropriate'])

    violated_categories = list(regulation_evaluation_result['category'])

    if (not appropriate):
        violated_proposal = "Violated Categories: " + \
            str(violated_categories) + SEP + proposal

        generated_feedback = regulation_feedback(
            regulation_feedback_prompt=regulation_feedback_prompt,
            proposal=violated_proposal
        )

        return ProposalEvaluationResponseDto(
            evaluation_result=0,
            feedback=FeedbackDto(
                feedback_type=2,
                current_score=total_score,
                comment=generated_feedback,
                violations=violated_categories
            ),
            summary=SummaryDto(
                title="",
                content="",
                current_score=0.0,
                keyword=[]
            )
        )

    # Summary Generator
    generated_summary = summary_generator(
        proposal=proposal,
        summary_generation_prompt=summary_generation_prompt
    )

    return ProposalEvaluationResponseDto(
        evaluation_result=1,
        feedback=FeedbackDto(
            feedback_type=0,
            current_score=0.0,
            comment="",
            violations=[]
        ),
        summary=SummaryDto(
            title=generated_summary['title'],
            content=generated_summary['content'],
            keyword=generated_summary['keyword']
        )
    )


def summary_generation(request: SummaryGenerationRequestDto) -> ProposalEvaluationResponseDto:
    # Proposal retrieved from db
    proposal = request.title + SEP \
        + request.content + SEP \
        + request.media_type + SEP \
        + str(request.proposal_score) + SEP \
        + str(request.additional_features)
        

    # Prompt
    generation_prompt = GenerationPrompt
    summary_generation_prompt = generation_prompt.summary_generation_prompt.value

    # Generator Method
    generated_summary = summary_generator(
        proposal=proposal,
        summary_generation_prompt=summary_generation_prompt
    )

    return ProposalEvaluationResponseDto(
        evaluation_result=1,
        feedback=FeedbackDto(
            feedback_type=0,
            current_score=0.0,
            comment="",
            violations=[]
        ),
        summary=SummaryDto(
            title=generated_summary['title'],
            content=generated_summary['content'],
            keyword=generated_summary['keyword']
        )
    )

/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TrainingPlan } from '../models/TrainingPlan';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TrainingPlansService {
    /**
     * Get All Plans
     * @returns TrainingPlan Successful Response
     * @throws ApiError
     */
    public static getAllPlansPlansGet(): CancelablePromise<Array<TrainingPlan>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/plans',
        });
    }
    /**
     * Add Plan
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static addPlanPlansPost(
        requestBody: TrainingPlan,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/plans',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Plan
     * @param planId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updatePlanPlansPlanIdPut(
        planId: number,
        requestBody: TrainingPlan,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/plans/{plan_id}',
            path: {
                'plan_id': planId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Patch Plan
     * @param planId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static patchPlanPlansPlanIdPatch(
        planId: number,
        requestBody: TrainingPlan,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/plans/{plan_id}',
            path: {
                'plan_id': planId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Plan
     * @param planId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deletePlanPlansPlanIdDelete(
        planId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/plans/{plan_id}',
            path: {
                'plan_id': planId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
